using ProductIntelligence.Core.Notifications.Enums;

namespace ProductIntelligence.Core.Notifications.DTOs;

public class NotificationResponseDto
{
    public Guid Id { get; set; }

    public NotificationType Type { get; set; }

    public string Title { get; set; } = string.Empty;

    public string Message { get; set; } = string.Empty;

    public bool IsRead { get; set; }

    public DateTime CreatedAtUtc { get; set; }
}