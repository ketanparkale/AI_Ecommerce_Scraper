
using Microsoft.AspNetCore.Mvc;
using ProductIntelligence.Core.Watches.DTOs;
using ProductIntelligence.Core.Watches.Services;

namespace ProductIntelligence.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ProductWatchesController : ControllerBase
{
    private readonly ProductWatchService _watchService;

    public ProductWatchesController(ProductWatchService watchService)
    {
        _watchService = watchService;
    }

    [HttpPost]
    public async Task<IActionResult> CreateWatch(
        [FromQuery] Guid userId,
        [FromBody] CreateProductWatchRequestDto request,
        CancellationToken cancellationToken)
    {
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
        [FromQuery] Guid userId,
        CancellationToken cancellationToken)
    {
        if (userId == Guid.Empty)
            return BadRequest(new { message = "Invalid user ID." });

        var watches = await _watchService.GetUserWatchesAsync(
            userId,
            cancellationToken);

        return Ok(watches);
    }


    [HttpPatch("{watchId:guid}/pause")]
    public async Task<IActionResult> PauseWatch(
        Guid watchId,
        [FromQuery] Guid userId,
        CancellationToken cancellationToken)
    {
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
        [FromQuery] Guid userId,
        CancellationToken cancellationToken)
    {
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
        [FromQuery] Guid userId,
        CancellationToken cancellationToken)
    {
        var success = await _watchService.DeleteWatchAsync(
            watchId,
            userId,
            cancellationToken);

        if (!success)
            return NotFound(new { message = "Product watch not found." });

        return NoContent();
    }
}
