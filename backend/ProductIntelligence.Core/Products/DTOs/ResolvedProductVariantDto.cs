namespace ProductIntelligence.Core.Products.DTOs;

public class ResolvedProductVariantDto
{
    public Guid VariantId { get; set; }
    public string Color { get; set; } = string.Empty;
    public string Size { get; set; } = string.Empty;
    public decimal? CurrentPrice { get; set; }
    public bool IsAvailable { get; set; }
}
