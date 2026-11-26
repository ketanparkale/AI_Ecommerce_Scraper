namespace ProductIntelligence.Core.Products.DTOs;

public class ResolvedProductResponse
{
    public Guid ProductId { get; set; }
    public string ProductUrl { get; set; } = string.Empty;
    public string Platform { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public List<ResolvedProductVariantDto> Variants { get; set; } = [];
}
