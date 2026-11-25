using ProductIntelligence.Core.Notifications.Entities;

namespace ProductIntelligence.Core.Notifications.Interfaces;

public interface INotificationRepository
{
    Task AddAsync(
        Notification notification,
        CancellationToken cancellationToken = default);

    Task AddRangeAsync(
        IEnumerable<Notification> notifications,
        CancellationToken cancellationToken = default);

    Task<List<Notification>> GetByUserIdAsync(
        Guid userId,
        CancellationToken cancellationToken = default);

    Task<Notification?> GetByIdForUserAsync(
        Guid notificationId,
        Guid userId,
        CancellationToken cancellationToken = default);
}