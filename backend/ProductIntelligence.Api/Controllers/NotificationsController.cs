using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ProductIntelligence.Core.Notifications.Services;

namespace ProductIntelligence.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class NotificationsController : ControllerBase
{
    private readonly NotificationService _notificationService;

    public NotificationsController(
        NotificationService notificationService)
    {
        _notificationService = notificationService;
    }

    [HttpGet]
    public async Task<IActionResult> GetNotifications(
        CancellationToken cancellationToken)
    {
        if (!TryGetUserId(out var userId))
            return Unauthorized(new { message = "Valid user identity is missing." });

        var notifications =
            await _notificationService.GetUserNotificationsAsync(
                userId,
                cancellationToken
            );

        return Ok(notifications);
    }

    [HttpPatch("{notificationId:guid}/read")]
    public async Task<IActionResult> MarkAsRead(
        Guid notificationId,
        CancellationToken cancellationToken)
    {
        if (!TryGetUserId(out var userId))
            return Unauthorized(new { message = "Valid user identity is missing." });

        var success = await _notificationService.MarkAsReadAsync(
            notificationId,
            userId,
            cancellationToken
        );

        if (!success)
            return NotFound("Notification not found.");

        return NoContent();
    }

    private bool TryGetUserId(out Guid userId)
    {
        userId = Guid.Empty;

        var claim = User.FindFirst(ClaimTypes.NameIdentifier)
            ?? User.FindFirst("nameid")
            ?? User.FindFirst("sub")
            ?? User.FindFirst("UserId");

        return claim is not null
            && Guid.TryParse(claim.Value, out userId)
            && userId != Guid.Empty;
    }
}