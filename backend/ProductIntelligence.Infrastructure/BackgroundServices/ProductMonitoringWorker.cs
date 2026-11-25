
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using ProductIntelligence.Core.Products.Interfaces;
using ProductIntelligence.Core.Products.Services;

namespace ProductIntelligence.Infrastructure.BackgroundServices;

public class ProductMonitoringWorker : BackgroundService
{
    private readonly IServiceScopeFactory _scopeFactory;
    private readonly ILogger<ProductMonitoringWorker> _logger;

    private readonly TimeSpan _interval = TimeSpan.FromMinutes(30);

    public ProductMonitoringWorker(
        IServiceScopeFactory scopeFactory,
        ILogger<ProductMonitoringWorker> logger)
    {
        _scopeFactory = scopeFactory;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(
        CancellationToken stoppingToken)
    {
        _logger.LogInformation("Product monitoring worker started.");

        using var timer = new PeriodicTimer(_interval);

        try
        {
            // Run immediately on startup.
            do
            {
                await ProcessActiveProductsAsync(stoppingToken);

            } while (await timer.WaitForNextTickAsync(stoppingToken));
        }
        catch (OperationCanceledException)
            when (stoppingToken.IsCancellationRequested)
        {
            _logger.LogInformation("Product monitoring worker is stopping.");
        }
    }

    
    private async Task ProcessActiveProductsAsync(
        CancellationToken cancellationToken)
    {
        try
        {
            // 1. Retrieve distinct active product IDs.
            List<Guid> productIds;

            using (var scope = _scopeFactory.CreateScope())
            {
                var watchRepository = scope.ServiceProvider
                    .GetRequiredService<IProductWatchRepository>();

                productIds = await watchRepository
                    .GetDistinctActiveProductIdsAsync(cancellationToken);
            }

            _logger.LogInformation(
                "Found {Count} products to monitor.",
                productIds.Count);

            // 2. Refresh each product independently.
            foreach (var productId in productIds)
            {
                cancellationToken.ThrowIfCancellationRequested();

                using var scope = _scopeFactory.CreateScope();

                try
                {
                    var monitoringService = scope.ServiceProvider
                        .GetRequiredService<ProductMonitoringService>();

                    var processedVariants =
                        await monitoringService.RefreshProductAsync(
                            productId,
                            cancellationToken);

                    _logger.LogInformation(
                        "Product {ProductId} refreshed. Variants processed: {Count}",
                        productId,
                        processedVariants);
                }
                catch (OperationCanceledException)
                    when (cancellationToken.IsCancellationRequested)
                {
                    throw;
                }
                catch (Exception exception)
                {
                    _logger.LogError(
                        exception,
                        "Failed to refresh product {ProductId}.",
                        productId);
                }
            }
        }
        catch (OperationCanceledException)
            when (cancellationToken.IsCancellationRequested)
        {
            throw;
        }
        catch (Exception exception)
        {
            _logger.LogError(
                exception,
                "An error occurred during the product monitoring cycle.");
        }
    }

}
