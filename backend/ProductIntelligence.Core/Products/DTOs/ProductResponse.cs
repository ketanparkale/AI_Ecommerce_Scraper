
namespace ProductIntelligence.Core.Products.DTOs;

public class ProductResponse
{
    public Guid Id { get; set; }

    public string ProductUrl { get; set; } = string.Empty;

    public string Platform { get; set; } = string.Empty;

    public string? ExternalProductId { get; set; }

    public string Title { get; set; } = string.Empty;

    public DateTime CreatedAtUtc { get; set; }
}
