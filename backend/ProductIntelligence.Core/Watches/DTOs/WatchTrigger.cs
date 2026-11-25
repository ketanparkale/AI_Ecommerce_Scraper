namespace ProductIntelligence.Core.Watches.DTOs;

public enum WatchTriggerType
{
    Price,
    Availability
}

public record WatchTrigger(
    Guid WatchId,
    Guid UserId,
    Guid ProductVariantId,
    WatchTriggerType Type,
    decimal? CurrentPrice
);