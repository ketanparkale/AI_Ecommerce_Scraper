using ProductIntelligence.Core.Common;
using ProductIntelligence.Core.Notifications.Entities;
using ProductIntelligence.Core.Notifications.Enums;
using ProductIntelligence.Core.Notifications.Interfaces;
using ProductIntelligence.Core.Watches.DTOs;
using ProductIntelligence.Core.Notifications.DTOs;

namespace ProductIntelligence.Core.Notifications.Services;

public class NotificationService
{
    private readonly INotificationRepository _notificationRepository;
    private readonly IUnitOfWork _unitOfWork;

    public NotificationService(
        INotificationRepository notificationRepository,
        IUnitOfWork unitOfWork)
    {
        _notificationRepository = notificationRepository;
        _unitOfWork = unitOfWork;
    }

    public async Task<int> CreateNotificationsAsync(
        List<WatchTrigger> triggers,
        CancellationToken cancellationToken = default)
    {
        if (triggers.Count == 0)
            return 0;

        var notifications = new List<Notification>();

        foreach (var trigger in triggers)
        {
            string title;
            string message;
            NotificationType type;

            switch (trigger.Type)
            {
                case WatchTriggerType.Price:
                    type = NotificationType.PriceDrop;
                    title = "Price target reached";
                    message = trigger.CurrentPrice.HasValue
                        ? $"Your watched product's price has reached ₹{trigger.CurrentPrice.Value:N2}."
                        : "Your watched product has reached its target price.";
                    break;

                case WatchTriggerType.Availability:
                    type = NotificationType.Availability;
                    title = "Product available";
                    message = "Your watched product variant is now available.";
                    break;

                default:
                    throw new ArgumentOutOfRangeException(
                        nameof(trigger.Type),
                        trigger.Type,
                        "Unsupported watch trigger type.");
            }

            notifications.Add(new Notification(
                trigger.UserId,
                trigger.WatchId,
                type,
                title,
                message
            ));
        }

        await _notificationRepository.AddRangeAsync(
            notifications,
            cancellationToken
        );

        return notifications.Count;
    }

    public async Task<List<NotificationResponseDto>> GetUserNotificationsAsync(
        Guid userId,
        CancellationToken cancellationToken = default)
    {
        var notifications = await _notificationRepository.GetByUserIdAsync(
            userId,
            cancellationToken
        );

        return notifications.Select(n => new NotificationResponseDto
        {
            Id = n.Id,
            Type = n.Type,
            Title = n.Title,
            Message = n.Message,
            IsRead = n.IsRead,
            CreatedAtUtc = n.CreatedAtUtc
        }).ToList();
    }

    // Mark a notification as read
    public async Task<bool> MarkAsReadAsync(
        Guid notificationId,
        Guid userId,
        CancellationToken cancellationToken = default)
    {
        var notification = await _notificationRepository.GetByIdForUserAsync(
            notificationId,
            userId,
            cancellationToken
        );

        if (notification is null)
            return false;

        if (notification.IsRead)
            return true;

        notification.MarkAsRead();

        await _unitOfWork.SaveChangesAsync(cancellationToken);

        return true;
    }
}