
using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ProductIntelligence.Core.Watches.DTOs;
using ProductIntelligence.Core.Watches.Services;

namespace ProductIntelligence.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class ProductWatchesController : ControllerBase
{
    private readonly ProductWatchService _watchService;

    public ProductWatchesController(ProductWatchService watchService)
    {
        _watchService = watchService;
    }

    [HttpPost]
    public async Task<IActionResult> CreateWatch(
        [FromBody] CreateProductWatchRequestDto request,
        CancellationToken cancellationToken)
    {
        if (!TryGetUserId(out var userId))
            return Unauthorized(new { message = "Valid user identity is missing." });

        try
        {
            var watchId = await _watchService.CreateWatchAsync(
                userId,
                request,
                cancellationToken);

            return Created(
                $"/api/productwatches/{watchId}",
                new { watchId });
        }
        catch (KeyNotFoundException exception)
        {
            return NotFound(new { message = exception.Message });
        }
        catch (ArgumentException exception)
        {
            return BadRequest(new { message = exception.Message });
        }
    }


    [HttpGet]
    public async Task<IActionResult> GetUserWatches(
        CancellationToken cancellationToken)
    {
        if (!TryGetUserId(out var userId))
            return Unauthorized(new { message = "Valid user identity is missing." });

        var watches = await _watchService.GetUserWatchesAsync(
            userId,
            cancellationToken);

        return Ok(watches);
    }


    [HttpPatch("{watchId:guid}/pause")]
    public async Task<IActionResult> PauseWatch(
        Guid watchId,
        CancellationToken cancellationToken)
    {
        if (!TryGetUserId(out var userId))
            return Unauthorized(new { message = "Valid user identity is missing." });

        var success = await _watchService.PauseWatchAsync(
            watchId,
            userId,
            cancellationToken);

        if (!success)
            return NotFound(new { message = "Product watch not found." });

        return NoContent();
    }

    [HttpPatch("{watchId:guid}/resume")]
    public async Task<IActionResult> ResumeWatch(
        Guid watchId,
        CancellationToken cancellationToken)
    {
        if (!TryGetUserId(out var userId))
            return Unauthorized(new { message = "Valid user identity is missing." });

        var success = await _watchService.ResumeWatchAsync(
            watchId,
            userId,
            cancellationToken);

        if (!success)
            return NotFound(new { message = "Product watch not found." });

        return NoContent();
    }

    [HttpDelete("{watchId:guid}")]
    public async Task<IActionResult> DeleteWatch(
        Guid watchId,
        CancellationToken cancellationToken)
    {
        if (!TryGetUserId(out var userId))
            return Unauthorized(new { message = "Valid user identity is missing." });

        var success = await _watchService.DeleteWatchAsync(
            watchId,
            userId,
            cancellationToken);

        if (!success)
            return NotFound(new { message = "Product watch not found." });

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
