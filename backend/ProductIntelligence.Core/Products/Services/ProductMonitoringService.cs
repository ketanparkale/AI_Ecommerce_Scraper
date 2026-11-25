using Microsoft.Extensions.Logging;
using ProductIntelligence.Core.Common;
using ProductIntelligence.Core.Products.DTOs;
using ProductIntelligence.Core.Products.Entities;
using ProductIntelligence.Core.Products.Interfaces;
using ProductIntelligence.Core.Watches.Services;
using ProductIntelligence.Core.Notifications.Services;

using ProductIntelligence.Core.Tests;

namespace ProductIntelligence.Core.Products.Services;

public class ProductMonitoringService
{
    private readonly IProductVariantRepository _variantRepository;
    private readonly IProductPriceHistoryRepository _priceHistoryRepository;
    private readonly IUnitOfWork _unitOfWork;
    private readonly IProductRepository _productRepository;
    private readonly IProductScraperClient _scraperClient;
    private readonly WatchEvaluationService _watchEvaluationService;
    private readonly NotificationService _notificationService;
    private readonly ILogger<ProductMonitoringService> _logger;

    public ProductMonitoringService(
        IProductRepository productRepository,
        IProductScraperClient scraperClient,
        IProductVariantRepository variantRepository,
        IProductPriceHistoryRepository priceHistoryRepository,
        IUnitOfWork unitOfWork,
        WatchEvaluationService watchEvaluationService,
        NotificationService notificationService,
        ILogger<ProductMonitoringService> logger)
    {
        _productRepository = productRepository;
        _scraperClient = scraperClient;
        _variantRepository = variantRepository;
        _priceHistoryRepository = priceHistoryRepository;
        _unitOfWork = unitOfWork;
        _watchEvaluationService = watchEvaluationService;
        _notificationService = notificationService;
        _logger = logger;
    }

    public async Task<int> ProcessScrapedProductAsync(
        Guid productId,
        ScrapedProductDto scrapedProduct,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(scrapedProduct);

        var historyRecords = new List<ProductPriceHistory>();
        var processedVariants = 0;

        foreach (var color in scrapedProduct.Colors)
        {
            foreach (var size in color.Sizes)
            {
                var variant = await _variantRepository
                    .GetByProductAndAttributesAsync(
                        productId,
                        color.Color,
                        size.Size,
                        cancellationToken);

                if (variant is null)
                {
                    variant = new ProductVariant(
                        productId: productId,
                        color: color.Color,
                        size: size.Size,
                        price: size.Price,
                        isAvailable: size.Available,
                        colorExternalId: color.Pid,
                        sizeExternalId: size.Pid
                    );

                    await _variantRepository.AddAsync(
                        variant,
                        cancellationToken);

                    // Initial observation establishes the baseline.
                    historyRecords.Add(
                        new ProductPriceHistory(
                            variant.Id,
                            size.Price,
                            size.Available
                        )
                    );
                }
                else
                {
                    bool changed = variant.UpdateObservation(
                        size.Price,
                        size.Available,
                        color.Pid,
                        size.Pid
                    );

                    if (changed)
                    {
                        historyRecords.Add(
                            new ProductPriceHistory(
                                variant.Id,
                                variant.CurrentPrice,
                                variant.IsAvailable
                            )
                        );
                    }
                }

                processedVariants++;
            }
        }

        await _priceHistoryRepository.AddRangeAsync(
            historyRecords,
            cancellationToken);

        return processedVariants;
    }


    public async Task<int> RefreshProductAsync(
        Guid productId,
        CancellationToken cancellationToken = default)
    {
        // 1. Retrieve product.
        var product = await _productRepository.GetByIdAsync(
            productId,
            cancellationToken
        );

        if (product is null)
        {
            throw new KeyNotFoundException(
                $"Product with ID '{productId}' was not found."
            );
        }

        // 2. Scrape latest product information.
        var scrapedProduct = await _scraperClient.ScrapeProductAsync(
            product.ProductUrl,
            cancellationToken
        );

        // 3. Stage variant and price history changes.
        var processedVariants = await ProcessScrapedProductAsync(
            productId,
            scrapedProduct,
            cancellationToken
        );

        // 4. Evaluate active watches.
        var triggers = await _watchEvaluationService.EvaluateProductAsync(
            productId,
            cancellationToken
        );

        // 5. Stage notification records.
        var notificationsCreated =
            await _notificationService.CreateNotificationsAsync(
                triggers,
                cancellationToken
            );

        // 6. Commit all database changes together.
        await _unitOfWork.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Product {ProductId} refreshed. Variants processed: {VariantCount}. Notifications created: {NotificationCount}.",
            productId,
            processedVariants,
            notificationsCreated
        );

        return processedVariants;
    }
}
