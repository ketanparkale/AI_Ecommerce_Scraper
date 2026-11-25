
using ProductIntelligence.Core.Products.Entities;

namespace ProductIntelligence.Core.Products.Interfaces;

public interface IProductRepository
{
    Task<Product?> GetByIdAsync(
        Guid id,
        CancellationToken cancellationToken = default);

    Task<Product?> GetByUrlAsync(
        string productUrl,
        CancellationToken cancellationToken = default);

    Task AddAsync(
        Product product,
        CancellationToken cancellationToken = default);
}
