using System.Net.Http.Json;
using ProductIntelligence.Core.Products.DTOs;
using ProductIntelligence.Core.Products.Interfaces;

namespace ProductIntelligence.Infrastructure.Scraping;

public class ProductScraperClient : IProductScraperClient
{
    private readonly HttpClient _httpClient;

    public ProductScraperClient(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    public async Task<ScrapedProductDto> ScrapeProductAsync(
        string productUrl,
        CancellationToken cancellationToken = default)
    {
        var response = await _httpClient.GetAsync(
            $"scrape/product?product_url={Uri.EscapeDataString(productUrl)}",
            cancellationToken
        );

        response.EnsureSuccessStatusCode();

        var result = await response.Content.ReadFromJsonAsync<ScrapedProductDto>(
            cancellationToken: cancellationToken
        );

        return result ?? throw new InvalidOperationException(
            "Python scraper returned an empty response."
        );
    }
}