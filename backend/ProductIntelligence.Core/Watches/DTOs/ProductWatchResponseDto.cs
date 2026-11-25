namespace ProductIntelligence.Core.Watches.DTOs;

public class ProductWatchResponseDto
{
    public Guid Id { get; set; }

    public Guid ProductVariantId { get; set; }

    public string Color { get; set; } = string.Empty;

    public string Size { get; set; } = string.Empty;

    public decimal? TargetPrice { get; set; }

    public bool MonitorPrice { get; set; }

    public bool MonitorAvailability { get; set; }

    public bool IsActive { get; set; }

    public DateTime CreatedAtUtc { get; set; }

    public DateTime? LastCheckedAtUtc { get; set; }

    public DateTime? LastNotifiedAtUtc { get; set; }
}