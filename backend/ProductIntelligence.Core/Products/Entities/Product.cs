namespace ProductIntelligence.Core.Products.Entities;

public class Product
{
    public Guid Id { get; private set; }
    public string ProductUrl { get; private set; } = string.Empty;
    public string Platform { get; private set; } = string.Empty;
    public string? ExternalProductId { get; private set; }
    public string Title { get; private set; } = string.Empty;
    public DateTime CreatedAtUtc { get; private set; }
    public DateTime UpdatedAtUtc { get; private set; }

    // Required by Entity Framework Core.
    private Product() { }

    public Product(
        string productUrl,
        string platform,
        string title,
        string? externalProductId = null)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(productUrl);
        ArgumentException.ThrowIfNullOrWhiteSpace(platform);
        ArgumentException.ThrowIfNullOrWhiteSpace(title);

        Id = Guid.NewGuid();
        ProductUrl = productUrl.Trim();
        Platform = platform.Trim().ToLowerInvariant();
        Title = title.Trim();
        ExternalProductId = string.IsNullOrWhiteSpace(externalProductId)
            ? null
            : externalProductId.Trim();

        CreatedAtUtc = UpdatedAtUtc = DateTime.UtcNow;
    }

    public void UpdateDetails(string title)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(title);

        Title = title.Trim();
        UpdatedAtUtc = DateTime.UtcNow;
    }
}