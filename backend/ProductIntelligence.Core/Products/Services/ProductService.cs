
using ProductIntelligence.Core.Products.Entities;
using ProductIntelligence.Core.Products.Interfaces;
using ProductIntelligence.Core.Common;

namespace ProductIntelligence.Core.Products.Services;

public class ProductService
{
    private readonly IProductRepository _repository;
    private readonly IUnitOfWork _unitOfWork;

    public ProductService(
        IProductRepository repository,
        IUnitOfWork unitOfWork)
    {
        _repository = repository;
        _unitOfWork = unitOfWork;
    }

    public async Task<Product> CreateAsync(
        string productUrl,
        string platform,
        string title,
        string? externalProductId = null,
        CancellationToken cancellationToken = default)
    {
        // Check whether the product already exists.
        var existingProduct = await _repository.GetByUrlAsync(
            productUrl,
            cancellationToken);

        if (existingProduct is not null)
        {
            throw new InvalidOperationException(
                "A product with this URL already exists.");
        }

        // Create the product entity.
        var product = new Product(
            productUrl,
            platform,
            title,
            externalProductId);

        await _repository.AddAsync(product, cancellationToken);
        await _unitOfWork.SaveChangesAsync(cancellationToken);

        return product;
    }

    public async Task<Product?> GetByIdAsync(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        return await _repository.GetByIdAsync(
            id,
            cancellationToken);
    }
}
