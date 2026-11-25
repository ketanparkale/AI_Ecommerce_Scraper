using ProductIntelligence.Core.Products.Entities;

namespace ProductIntelligence.Core.Products.Interfaces;

public interface IProductPriceHistoryRepository
{
    Task AddAsync(
        ProductPriceHistory history,
        CancellationToken cancellationToken = default);

    Task AddRangeAsync(
        IEnumerable<ProductPriceHistory> history,
        CancellationToken cancellationToken = default);
}