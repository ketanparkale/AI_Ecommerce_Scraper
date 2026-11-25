using Microsoft.AspNetCore.Mvc;
using ProductIntelligence.Core.Notifications.Services;

namespace ProductIntelligence.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class NotificationsController : ControllerBase
{
    private readonly NotificationService _notificationService;

    public NotificationsController(
        NotificationService notificationService)
    {
        _notificationService = notificationService;
    }

    // GET: api/notifications?userId={guid}
    [HttpGet]
    public async Task<IActionResult> GetNotifications(
        [FromQuery] Guid userId,
        CancellationToken cancellationToken)
    {
        if (userId == Guid.Empty)
            return BadRequest("A valid userId is required.");

        var notifications =
            await _notificationService.GetUserNotificationsAsync(
                userId,
                cancellationToken
            );

        return Ok(notifications);
    }

    // PATCH: api/notifications/{notificationId}/read?userId={guid}
    [HttpPatch("{notificationId:guid}/read")]
    public async Task<IActionResult> MarkAsRead(
        Guid notificationId,
        [FromQuery] Guid userId,
        CancellationToken cancellationToken)
    {
        if (userId == Guid.Empty)
            return BadRequest("A valid userId is required.");

        var success = await _notificationService.MarkAsReadAsync(
            notificationId,
            userId,
            cancellationToken
        );

        if (!success)
            return NotFound("Notification not found.");

        return NoContent();
    }
}