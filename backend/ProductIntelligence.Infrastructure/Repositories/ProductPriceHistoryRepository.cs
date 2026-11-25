
using ProductIntelligence.Core.Products.Entities;
using ProductIntelligence.Core.Products.Interfaces;
using ProductIntelligence.Infrastructure.Data;

namespace ProductIntelligence.Infrastructure.Repositories;

public class ProductPriceHistoryRepository : IProductPriceHistoryRepository
{
    private readonly ApplicationDbContext _context;

    public ProductPriceHistoryRepository(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task AddAsync(
    ProductPriceHistory history,
    CancellationToken cancellationToken = default)
    {
        await _context.ProductPriceHistories.AddAsync(
            history,
            cancellationToken);
    }

    public async Task AddRangeAsync(
        IEnumerable<ProductPriceHistory> history,
        CancellationToken cancellationToken = default)
    {
        await _context.ProductPriceHistories.AddRangeAsync(
            history,
            cancellationToken);
    }
}
