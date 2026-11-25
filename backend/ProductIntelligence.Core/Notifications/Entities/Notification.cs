using ProductIntelligence.Core.Notifications.Enums;

namespace ProductIntelligence.Core.Notifications.Entities;

public class Notification
{
    public Guid Id { get; private set; }

    public Guid UserId { get; private set; }

    public Guid ProductWatchId { get; private set; }

    public NotificationType Type { get; private set; }

    public string Title { get; private set; } = string.Empty;

    public string Message { get; private set; } = string.Empty;

    public bool IsRead { get; private set; }

    public DateTime CreatedAtUtc { get; private set; }

    private Notification() { }

    public Notification(
        Guid userId,
        Guid productWatchId,
        NotificationType type,
        string title,
        string message)
    {
        if (string.IsNullOrWhiteSpace(title))
            throw new ArgumentException("Title is required.", nameof(title));

        if (string.IsNullOrWhiteSpace(message))
            throw new ArgumentException("Message is required.", nameof(message));

        Id = Guid.NewGuid();
        UserId = userId;
        ProductWatchId = productWatchId;
        Type = type;
        Title = title;
        Message = message;
        IsRead = false;
        CreatedAtUtc = DateTime.UtcNow;
    }

    public void MarkAsRead()
    {
        IsRead = true;
    }
}