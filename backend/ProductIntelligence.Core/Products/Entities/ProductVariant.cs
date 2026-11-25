
namespace ProductIntelligence.Core.Products.Entities;

public class ProductVariant
{
    public Guid Id { get; private set; }

    public Guid ProductId { get; private set; }

    public string Color { get; private set; } = string.Empty;

    public string Size { get; private set; } = string.Empty;

    public string? ColorExternalId { get; private set; }

    public string? SizeExternalId { get; private set; }

    public decimal? CurrentPrice { get; private set; }

    public decimal? MinPrice { get; private set; }

    public decimal? MaxPrice { get; private set; }

    public bool IsAvailable { get; private set; }

    public DateTime LastUpdatedAtUtc { get; private set; }

    public DateTime? LastChangedAtUtc { get; private set; }

    private ProductVariant() { }

    public ProductVariant(
        Guid productId,
        string color,
        string size,
        decimal? price,
        bool isAvailable,
        string? colorExternalId = null,
        string? sizeExternalId = null)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(color);
        ArgumentException.ThrowIfNullOrWhiteSpace(size);

        if (price < 0)
            throw new ArgumentOutOfRangeException(nameof(price));

        Id = Guid.NewGuid();
        ProductId = productId;
        Color = color.Trim();
        Size = size.Trim();

        ColorExternalId = colorExternalId;
        SizeExternalId = sizeExternalId;

        CurrentPrice = price;
        MinPrice = price;
        MaxPrice = price;

        IsAvailable = isAvailable;

        LastUpdatedAtUtc = DateTime.UtcNow;
        LastChangedAtUtc = LastUpdatedAtUtc;
    }

    public bool UpdateObservation(
        decimal? newPrice,
        bool newAvailability,
        string? colorExternalId = null,
        string? sizeExternalId = null)
    {
        if (newPrice < 0)
            throw new ArgumentOutOfRangeException(nameof(newPrice));

        // A missing price should not count as a price change.
        bool priceChanged =
            newPrice.HasValue && CurrentPrice != newPrice;

        bool availabilityChanged =
            IsAvailable != newAvailability;

        bool hasChanged = priceChanged || availabilityChanged;

        if (newPrice.HasValue)
        {
            CurrentPrice = newPrice;

            MinPrice = MinPrice.HasValue
                ? Math.Min(MinPrice.Value, newPrice.Value)
                : newPrice;

            MaxPrice = MaxPrice.HasValue
                ? Math.Max(MaxPrice.Value, newPrice.Value)
                : newPrice;
        }

        if (!string.IsNullOrWhiteSpace(colorExternalId))
            ColorExternalId = colorExternalId;

        if (!string.IsNullOrWhiteSpace(sizeExternalId))
            SizeExternalId = sizeExternalId;

        IsAvailable = newAvailability;
        LastUpdatedAtUtc = DateTime.UtcNow;

        if (hasChanged)
            LastChangedAtUtc = LastUpdatedAtUtc;

        return hasChanged;
    }
}
