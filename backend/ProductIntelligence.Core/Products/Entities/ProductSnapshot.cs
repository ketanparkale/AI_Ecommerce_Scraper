
namespace ProductIntelligence.Core.Products.Entities;

public class ProductSnapshot
{
    public Guid Id { get; private set; }

    public Guid ProductId { get; private set; }

    public DateTime CapturedAtUtc { get; private set; }

    public ICollection<ProductVariantSnapshot> Variants { get; private set; }
        = new List<ProductVariantSnapshot>();

    private ProductSnapshot() { }

    public ProductSnapshot(Guid productId)
    {
        Id = Guid.NewGuid();
        ProductId = productId;
        CapturedAtUtc = DateTime.UtcNow;
    }
}
