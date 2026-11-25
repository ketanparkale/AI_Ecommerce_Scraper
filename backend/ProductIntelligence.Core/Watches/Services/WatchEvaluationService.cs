using ProductIntelligence.Core.Products.Interfaces;
using ProductIntelligence.Core.Watches.DTOs;

namespace ProductIntelligence.Core.Watches.Services;

public class WatchEvaluationService
{
    private readonly IProductWatchRepository _watchRepository;

    public WatchEvaluationService(
        IProductWatchRepository watchRepository
        )
    {
        _watchRepository = watchRepository;
    }

    public async Task<List<WatchTrigger>> EvaluateProductAsync(
        Guid productId,
        CancellationToken cancellationToken = default)
    {
        var watches = await _watchRepository.GetActiveByProductIdAsync(
            productId,
            cancellationToken
        );

        var triggers = new List<WatchTrigger>();
        bool notificationGenerated = false;

        foreach (var watch in watches)
        {
            var variant = watch.ProductVariant;

            // Evaluate price only when a price is available.
            if (variant.CurrentPrice.HasValue)
            {
                bool shouldNotifyPrice =
                    watch.ShouldNotifyPrice(variant.CurrentPrice.Value);

                if (shouldNotifyPrice)
                {   
                    notificationGenerated = true;

                    triggers.Add(new WatchTrigger(
                        watch.Id,
                        watch.UserId,
                        watch.ProductVariantId,
                        WatchTriggerType.Price,
                        variant.CurrentPrice
                    ));
                }
            }

            // Evaluate availability independently.
            bool shouldNotifyAvailability =
                watch.ShouldNotifyAvailability(variant.IsAvailable);

            if (shouldNotifyAvailability)
            {
                notificationGenerated = true;

                triggers.Add(new WatchTrigger(
                    watch.Id,
                    watch.UserId,
                    watch.ProductVariantId,
                    WatchTriggerType.Availability,
                    variant.CurrentPrice
                ));
            }
            
            if (notificationGenerated)
            {
                watch.MarkNotified();
            }

            watch.MarkChecked();
        }


        return triggers;
    }
}