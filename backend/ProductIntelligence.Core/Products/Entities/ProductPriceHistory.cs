
namespace ProductIntelligence.Core.Products.Entities;

public class ProductPriceHistory
{
    public Guid Id { get; private set; }

    public Guid ProductVariantId { get; private set; }

    public decimal? Price { get; private set; }

    public bool IsAvailable { get; private set; }

    public DateTime ObservedAtUtc { get; private set; }

    public ProductVariant ProductVariant { get; private set; } = null!;

    private ProductPriceHistory() { }

    public ProductPriceHistory(
        Guid productVariantId,
        decimal? price,
        bool isAvailable)
    {
        if (price < 0)
            throw new ArgumentOutOfRangeException(nameof(price));

        Id = Guid.NewGuid();
        ProductVariantId = productVariantId;
        Price = price;
        IsAvailable = isAvailable;
        ObservedAtUtc = DateTime.UtcNow;
    }
}
