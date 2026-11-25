using Microsoft.EntityFrameworkCore;
using ProductIntelligence.Core.Products.Interfaces;
using ProductIntelligence.Core.Watches.Entities;
using ProductIntelligence.Infrastructure.Data;

namespace ProductIntelligence.Infrastructure.Repositories
{
    public class ProductWatchRepository : IProductWatchRepository
    {
        private readonly ApplicationDbContext _context;

        public ProductWatchRepository(ApplicationDbContext context)
        {
            _context = context;
        }

        public async Task<List<Guid>> GetDistinctActiveProductIdsAsync(
            CancellationToken cancellationToken = default)
        {
            return await _context.ProductWatches
                .AsNoTracking()
                .Where(watch => watch.IsActive)
                .Select(watch => watch.ProductVariant.ProductId)
                .Distinct()
                .ToListAsync(cancellationToken);
        }

        public async Task<List<ProductWatch>> GetActiveByProductIdAsync(
            Guid productId,
            CancellationToken cancellationToken = default)
        {
            return await _context.ProductWatches
                .Include(watch => watch.ProductVariant)
                .Where(watch =>
                    watch.IsActive &&
                    watch.ProductVariant.ProductId == productId)
                .ToListAsync(cancellationToken);
        }

        public async Task AddAsync(
            ProductWatch watch,
            CancellationToken cancellationToken = default)
        {
            await _context.ProductWatches.AddAsync(
                watch,
                cancellationToken);
        }

        public async Task<List<ProductWatch>> GetByUserIdAsync(
            Guid userId,
            CancellationToken cancellationToken = default)
        {
            return await _context.ProductWatches
                .AsNoTracking()
                .Include(watch => watch.ProductVariant)
                .Where(watch => watch.UserId == userId)
                .OrderByDescending(watch => watch.CreatedAtUtc)
                .ToListAsync(cancellationToken);
        }

        public async Task<ProductWatch?> GetByIdForUserAsync(
            Guid watchId,
            Guid userId,
            CancellationToken cancellationToken = default)
        {
            return await _context.ProductWatches
                .FirstOrDefaultAsync(
                    watch => watch.Id == watchId &&
                            watch.UserId == userId,
                    cancellationToken);
        }

        public void Delete(ProductWatch watch)
        {
            _context.ProductWatches.Remove(watch);
        }
    }
}