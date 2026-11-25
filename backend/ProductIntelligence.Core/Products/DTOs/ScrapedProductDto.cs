namespace ProductIntelligence.Core.Products.DTOs;

public class ScrapedProductDto
{
    public string Title { get; set; } = string.Empty;
    public string? Brand { get; set; }
    public List<ColorVariantDto> Colors { get; set; } = [];
}