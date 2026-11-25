
using ProductIntelligence.Core.Common;
using ProductIntelligence.Core.Products.Interfaces;
using ProductIntelligence.Core.Watches.DTOs;
using ProductIntelligence.Core.Watches.Entities;

namespace ProductIntelligence.Core.Watches.Services;

public class ProductWatchService
{
    private readonly IProductWatchRepository _watchRepository;
    private readonly IProductVariantRepository _variantRepository;
    private readonly IUnitOfWork _unitOfWork;

    public ProductWatchService(
        IProductWatchRepository watchRepository,
        IProductVariantRepository variantRepository,
        IUnitOfWork unitOfWork)
    {
        _watchRepository = watchRepository;
        _variantRepository = variantRepository;
        _unitOfWork = unitOfWork;
    }

    public async Task<Guid> CreateWatchAsync(
        Guid userId,
        CreateProductWatchRequestDto request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);

        if (userId == Guid.Empty)
            throw new ArgumentException("Invalid user ID.");

        var variant = await _variantRepository.GetByIdAsync(
            request.ProductVariantId,
            cancellationToken);

        if (variant is null)
            throw new KeyNotFoundException("Product variant not found.");

        var watch = new ProductWatch(
            userId,
            variant.Id,
            request.TargetPrice,
            request.MonitorPrice,
            request.MonitorAvailability);

        await _watchRepository.AddAsync(
            watch,
            cancellationToken);

        await _unitOfWork.SaveChangesAsync(cancellationToken);

        return watch.Id;
    }


    public async Task<List<ProductWatchResponseDto>> GetUserWatchesAsync(
        Guid userId,
        CancellationToken cancellationToken = default)
    {
        var watches = await _watchRepository.GetByUserIdAsync(
            userId,
            cancellationToken);

        return watches.Select(watch => new ProductWatchResponseDto
        {
            Id = watch.Id,
            ProductVariantId = watch.ProductVariantId,
            Color = watch.ProductVariant.Color,
            Size = watch.ProductVariant.Size,
            TargetPrice = watch.TargetPrice,
            MonitorPrice = watch.MonitorPrice,
            MonitorAvailability = watch.MonitorAvailability,
            IsActive = watch.IsActive,
            CreatedAtUtc = watch.CreatedAtUtc,
            LastCheckedAtUtc = watch.LastCheckedAtUtc,
            LastNotifiedAtUtc = watch.LastNotifiedAtUtc
        }).ToList();
    }

    public async Task<bool> PauseWatchAsync(
        Guid watchId,
        Guid userId,
        CancellationToken cancellationToken = default)
    {
        var watch = await _watchRepository.GetByIdForUserAsync(
            watchId,
            userId,
            cancellationToken);

        if (watch is null)
            return false;

        watch.Pause();

        await _unitOfWork.SaveChangesAsync(cancellationToken);

        return true;
    }

    public async Task<bool> ResumeWatchAsync(
        Guid watchId,
        Guid userId,
        CancellationToken cancellationToken = default)
    {
        var watch = await _watchRepository.GetByIdForUserAsync(
            watchId,
            userId,
            cancellationToken);

        if (watch is null)
            return false;

        watch.Resume();

        await _unitOfWork.SaveChangesAsync(cancellationToken);

        return true;
    }


    public async Task<bool> DeleteWatchAsync(
        Guid watchId,
        Guid userId,
        CancellationToken cancellationToken = default)
    {
        var watch = await _watchRepository.GetByIdForUserAsync(
            watchId,
            userId,
            cancellationToken);

        if (watch is null)
            return false;

        _watchRepository.Delete(watch);

        await _unitOfWork.SaveChangesAsync(cancellationToken);

        return true;
    }
}
