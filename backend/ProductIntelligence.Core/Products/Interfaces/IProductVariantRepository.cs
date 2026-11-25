using ProductIntelligence.Core.Products.Entities;

namespace ProductIntelligence.Core.Products.Interfaces;

public interface IProductVariantRepository
{
    Task<ProductVariant?> GetByIdAsync(
        Guid id,
        CancellationToken cancellationToken = default);

    Task<ProductVariant?> GetByProductAndAttributesAsync(
        Guid productId,
        string color,
        string size,
        CancellationToken cancellationToken = default);

    Task<List<ProductVariant>> GetByProductIdAsync(
        Guid productId,
        CancellationToken cancellationToken = default);

    Task AddAsync(
        ProductVariant variant,
        CancellationToken cancellationToken = default);

    Task UpdateAsync(
        ProductVariant variant,
        CancellationToken cancellationToken = default);
}