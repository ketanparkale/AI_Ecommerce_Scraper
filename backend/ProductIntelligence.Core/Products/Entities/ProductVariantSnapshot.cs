
namespace ProductIntelligence.Core.Products.Entities;

public class ProductVariantSnapshot
{
    public Guid Id { get; private set; }

    public Guid ProductSnapshotId { get; private set; }

    public string Color { get; private set; } = string.Empty;

    public string Size { get; private set; } = string.Empty;

    public decimal Price { get; private set; }

    public bool IsAvailable { get; private set; }

    public ProductSnapshot ProductSnapshot { get; private set; } = null!;

    private ProductVariantSnapshot() { }

    public ProductVariantSnapshot(
        Guid productSnapshotId,
        string color,
        string size,
        decimal price,
        bool isAvailable)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(color);
        ArgumentException.ThrowIfNullOrWhiteSpace(size);

        if (price < 0)
            throw new ArgumentOutOfRangeException(nameof(price));

        Id = Guid.NewGuid();
        ProductSnapshotId = productSnapshotId;
        Color = color.Trim();
        Size = size.Trim();
        Price = price;
        IsAvailable = isAvailable;
    }
}
