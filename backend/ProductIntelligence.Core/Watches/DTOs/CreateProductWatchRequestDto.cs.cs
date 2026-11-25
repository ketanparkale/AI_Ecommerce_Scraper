
namespace ProductIntelligence.Core.Watches.DTOs;

public class CreateProductWatchRequestDto
{
    public Guid ProductVariantId { get; set; }

    public decimal? TargetPrice { get; set; }

    public bool MonitorPrice { get; set; }

    public bool MonitorAvailability { get; set; }
}
