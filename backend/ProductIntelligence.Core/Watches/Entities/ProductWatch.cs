
using ProductIntelligence.Core.Products.Entities;

namespace ProductIntelligence.Core.Watches.Entities;

public class ProductWatch
{
    public Guid Id { get; private set; }

    public Guid UserId { get; private set; }

    public Guid ProductVariantId { get; private set; }

    public ProductVariant ProductVariant { get; private set; } = null!;

    public decimal? TargetPrice { get; private set; }

    public bool MonitorPrice { get; private set; }

    public bool MonitorAvailability { get; private set; }

    public bool PriceConditionMet { get; private set; }

    public bool AvailabilityConditionMet { get; private set; }

    public bool IsActive { get; private set; }

    public DateTime CreatedAtUtc { get; private set; }

    public DateTime? LastCheckedAtUtc { get; private set; }

    public DateTime? LastNotifiedAtUtc { get; private set; }

    private ProductWatch() { }

    public ProductWatch(
        Guid userId,
        Guid productVariantId,
        decimal? targetPrice,
        bool monitorPrice,
        bool monitorAvailability)
    {
        if (monitorPrice && !targetPrice.HasValue)
        {
            throw new ArgumentException(
                "Target price is required when price monitoring is enabled."
            );
        }

        if (targetPrice < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(targetPrice));
        }

        if (!monitorPrice && !monitorAvailability)
        {
            throw new ArgumentException(
                "At least one monitoring condition must be enabled."
            );
        }

        Id = Guid.NewGuid();
        UserId = userId;
        ProductVariantId = productVariantId;
        TargetPrice = targetPrice;
        MonitorPrice = monitorPrice;
        MonitorAvailability = monitorAvailability;

        PriceConditionMet = false;
        AvailabilityConditionMet = false;

        IsActive = true;
        CreatedAtUtc = DateTime.UtcNow;
    }

    public bool ShouldNotifyPrice(decimal currentPrice)
    {
        if (!MonitorPrice || !TargetPrice.HasValue)
            return false;

        bool conditionMet = currentPrice <= TargetPrice.Value;

        bool shouldNotify = !PriceConditionMet && conditionMet;

        PriceConditionMet = conditionMet;

        return shouldNotify;
    }

    public bool ShouldNotifyAvailability(bool isAvailable)
    {
        if (!MonitorAvailability)
            return false;

        bool conditionMet = isAvailable;

        bool shouldNotify =
            !AvailabilityConditionMet && conditionMet;

        AvailabilityConditionMet = conditionMet;

        return shouldNotify;
    }

    public void MarkChecked()
    {
        LastCheckedAtUtc = DateTime.UtcNow;
    }

    public void MarkNotified()
    {
        LastNotifiedAtUtc = DateTime.UtcNow;
    }

    public void Pause()
    {
        IsActive = false;
    }
    public void Resume()
    {
        IsActive = true;
    }
}
