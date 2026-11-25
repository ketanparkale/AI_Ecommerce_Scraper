using ProductIntelligence.Core.Products.Entities;

namespace ProductIntelligence.Core.Products.Interfaces;

public interface IProductSnapshotRepository
{
    Task AddAsync(
        ProductSnapshot snapshot,
        CancellationToken cancellationToken = default);

    Task<List<ProductSnapshot>> GetHistoryAsync(
        Guid productId,
        int limit = 20,
        CancellationToken cancellationToken = default);

    Task<ProductVariantSnapshot?> GetLatestVariantAsync(
        Guid productId,
        string color,
        string size,
        CancellationToken cancellationToken = default);
}