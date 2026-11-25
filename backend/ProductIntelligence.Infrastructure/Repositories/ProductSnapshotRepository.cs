using Microsoft.EntityFrameworkCore;
using ProductIntelligence.Core.Products.Entities;
using ProductIntelligence.Core.Products.Interfaces;
using ProductIntelligence.Infrastructure.Data;

namespace ProductIntelligence.Infrastructure.Repositories;

public class ProductSnapshotRepository : IProductSnapshotRepository
{
    private readonly ApplicationDbContext _context;

    public ProductSnapshotRepository(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task AddAsync(
        ProductSnapshot snapshot,
        CancellationToken cancellationToken = default)
    {
        await _context.ProductSnapshots.AddAsync(
            snapshot,
            cancellationToken);

        await _context.SaveChangesAsync(cancellationToken);
    }

    public async Task<List<ProductSnapshot>> GetHistoryAsync(
        Guid productId,
        int limit = 20,
        CancellationToken cancellationToken = default)
    {
        if (limit < 1)
            return [];

        return await _context.ProductSnapshots
            .AsNoTracking()
            .Where(snapshot => snapshot.ProductId == productId)
            .Include(snapshot => snapshot.Variants)
            .OrderByDescending(snapshot => snapshot.CapturedAtUtc)
            .Take(limit)
            .ToListAsync(cancellationToken);
    }

    public async Task<ProductVariantSnapshot?> GetLatestVariantAsync(
        Guid productId,
        string color,
        string size,
        CancellationToken cancellationToken = default)
    {
        return await _context.ProductVariantSnapshots
            .AsNoTracking()
            .Where(variant =>
                variant.ProductSnapshot.ProductId == productId &&
                variant.Color == color &&
                variant.Size == size)
            .OrderByDescending(variant =>
                variant.ProductSnapshot.CapturedAtUtc)
            .FirstOrDefaultAsync(cancellationToken);
    }
}