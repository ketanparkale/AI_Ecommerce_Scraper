
using ProductIntelligence.Core.Watches.Entities;
namespace ProductIntelligence.Core.Products.Interfaces;

public interface IProductWatchRepository
{
    Task<List<Guid>> GetDistinctActiveProductIdsAsync(
        CancellationToken cancellationToken = default
    );

    Task<List<ProductWatch>> GetActiveByProductIdAsync(
    Guid productId,
    CancellationToken cancellationToken = default);

    Task AddAsync(ProductWatch watch, CancellationToken cancellationToken = default);

    Task<List<ProductWatch>> GetByUserIdAsync(
    Guid userId,
    CancellationToken cancellationToken = default);

    Task<ProductWatch?> GetByIdForUserAsync(
    Guid watchId,
    Guid userId,
    CancellationToken cancellationToken = default);

    void Delete(ProductWatch watch);
}