
using Microsoft.EntityFrameworkCore;
using ProductIntelligence.Core.Products.Entities;
using ProductIntelligence.Core.Products.Interfaces;
using ProductIntelligence.Infrastructure.Data;

namespace ProductIntelligence.Infrastructure.Repositories;

public class ProductVariantRepository : IProductVariantRepository
{
    private readonly ApplicationDbContext _context;

    public ProductVariantRepository(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<ProductVariant?> GetByIdAsync(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        return await _context.ProductVariants
            .FirstOrDefaultAsync(
                v => v.Id == id,
                cancellationToken);
    }

    public async Task<ProductVariant?> GetByProductAndAttributesAsync(
        Guid productId,
        string color,
        string size,
        CancellationToken cancellationToken = default)
    {
        return await _context.ProductVariants
            .FirstOrDefaultAsync(
                v => v.ProductId == productId
                    && v.Color == color
                    && v.Size == size,
                cancellationToken);
    }

    public async Task<List<ProductVariant>> GetByProductIdAsync(
        Guid productId,
        CancellationToken cancellationToken = default)
    {
        return await _context.ProductVariants
            .Where(v => v.ProductId == productId)
            .ToListAsync(cancellationToken);
    }

    public async Task AddAsync(
    ProductVariant variant,
    CancellationToken cancellationToken = default)
    {
        await _context.ProductVariants.AddAsync(
            variant,
            cancellationToken);
    }

    public Task UpdateAsync(
    ProductVariant variant,
    CancellationToken cancellationToken = default)
    {
        _context.ProductVariants.Update(variant);
        return Task.CompletedTask;
    }
}
