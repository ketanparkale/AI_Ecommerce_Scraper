using ProductIntelligence.Core.Common;
using ProductIntelligence.Core.Products.DTOs;
using ProductIntelligence.Core.Products.Entities;
using ProductIntelligence.Core.Products.Interfaces;

namespace ProductIntelligence.Core.Products.Services;

public class ProductResolutionService
{
    private readonly IProductRepository _productRepository;
    private readonly IProductVariantRepository _variantRepository;
    private readonly IProductScraperClient _scraperClient;
    private readonly ProductMonitoringService _monitoringService;
    private readonly IUnitOfWork _unitOfWork;

    public ProductResolutionService(
        IProductRepository productRepository,
        IProductVariantRepository variantRepository,
        IProductScraperClient scraperClient,
        ProductMonitoringService monitoringService,
        IUnitOfWork unitOfWork)
    {
        _productRepository = productRepository;
        _variantRepository = variantRepository;
        _scraperClient = scraperClient;
        _monitoringService = monitoringService;
        _unitOfWork = unitOfWork;
    }

    public async Task<ResolvedProductResponse> ResolveAsync(
        string productUrl,
        CancellationToken cancellationToken = default)
    {
        var normalizedUrl = NormalizeAndValidateUrl(productUrl);

        var product = await _productRepository.GetByUrlAsync(
            normalizedUrl,
            cancellationToken);

        var scrapedProduct = await _scraperClient.ScrapeProductAsync(
            normalizedUrl,
            cancellationToken);

        ValidateScrapedProduct(scrapedProduct);

        if (product is null)
        {
            product = new Product(
                normalizedUrl,
                "flipkart",
                scrapedProduct.Title);

            await _productRepository.AddAsync(
                product,
                cancellationToken);
        }
        else if (!string.Equals(
            product.Title,
            scrapedProduct.Title,
            StringComparison.Ordinal))
        {
            product.UpdateDetails(scrapedProduct.Title);
        }

        await _monitoringService.ProcessScrapedProductAsync(
            product.Id,
            scrapedProduct,
            cancellationToken);

        await _unitOfWork.SaveChangesAsync(cancellationToken);

        var variants = await _variantRepository.GetByProductIdAsync(
            product.Id,
            cancellationToken);

        return new ResolvedProductResponse
        {
            ProductId = product.Id,
            ProductUrl = product.ProductUrl,
            Platform = product.Platform,
            Title = product.Title,
            Variants = variants.Select(variant =>
                new ResolvedProductVariantDto
                {
                    VariantId = variant.Id,
                    Color = variant.Color,
                    Size = variant.Size,
                    CurrentPrice = variant.CurrentPrice,
                    IsAvailable = variant.IsAvailable
                }).ToList()
        };
    }

    private static string NormalizeAndValidateUrl(string productUrl)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(productUrl);

        if (!Uri.TryCreate(productUrl.Trim(), UriKind.Absolute, out var uri))
        {
            throw new ArgumentException("Invalid product URL.");
        }

        if (uri.Scheme != Uri.UriSchemeHttps)
        {
            throw new ArgumentException("Only HTTPS product URLs are supported.");
        }

        if (!string.IsNullOrEmpty(uri.UserInfo))
        {
            throw new ArgumentException("Product URLs must not contain user credentials.");
        }

        var host = uri.Host.ToLowerInvariant();
        if (host != "flipkart.com"
            && !host.EndsWith(".flipkart.com", StringComparison.Ordinal))
        {
            throw new ArgumentException("Currently, only Flipkart product URLs are supported.");
        }

        if (!uri.IsDefaultPort)
        {
            throw new ArgumentException("Custom ports are not allowed in product URLs.");
        }

        var builder = new UriBuilder(uri) { Fragment = string.Empty };
        return builder.Uri.AbsoluteUri;
    }

    private static void ValidateScrapedProduct(ScrapedProductDto scrapedProduct)
    {
        ArgumentNullException.ThrowIfNull(scrapedProduct);

        if (string.IsNullOrWhiteSpace(scrapedProduct.Title))
        {
            throw new InvalidOperationException("The scraper did not return a valid product title.");
        }

        if (scrapedProduct.Colors is null || scrapedProduct.Colors.Count == 0)
        {
            throw new InvalidOperationException("The scraper did not return any product colors.");
        }

        foreach (var color in scrapedProduct.Colors)
        {
            if (color is null
                || string.IsNullOrWhiteSpace(color.Color)
                || color.Sizes is null
                || color.Sizes.Count == 0)
            {
                throw new InvalidOperationException("The scraper returned invalid color or size information.");
            }

            foreach (var size in color.Sizes)
            {
                if (size is null || string.IsNullOrWhiteSpace(size.Size))
                {
                    throw new InvalidOperationException("The scraper returned an invalid size variant.");
                }
            }
        }
    }
}
