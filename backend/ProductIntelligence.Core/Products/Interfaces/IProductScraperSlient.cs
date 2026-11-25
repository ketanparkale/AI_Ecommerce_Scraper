using ProductIntelligence.Core.Products.DTOs;

namespace ProductIntelligence.Core.Products.Interfaces;

public interface IProductScraperClient
{
    Task<ScrapedProductDto> ScrapeProductAsync(
        string productUrl,
        CancellationToken cancellationToken = default
    );
}