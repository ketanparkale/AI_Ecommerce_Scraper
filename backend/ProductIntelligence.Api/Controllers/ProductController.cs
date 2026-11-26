
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ProductIntelligence.Core.Products.DTOs;
using ProductIntelligence.Core.Products.Services;

namespace ProductIntelligence.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class ProductsController : ControllerBase
{
    private readonly ProductService _productService;
    private readonly ProductMonitoringService _monitoringService;
    private readonly ProductResolutionService _resolutionService;
    private readonly ILogger<ProductsController> _logger;

    public ProductsController(
        ProductService productService,
        ProductMonitoringService monitoringService,
        ProductResolutionService resolutionService,
        ILogger<ProductsController> logger)
    {
        _productService = productService;
        _monitoringService = monitoringService;
        _resolutionService = resolutionService;
        _logger = logger;
    }

    [HttpPost("resolve")]
    [ProducesResponseType(typeof(ResolvedProductResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status502BadGateway)]
    public async Task<ActionResult<ResolvedProductResponse>> ResolveProduct(
        [FromBody] ResolveProductRequest request,
        CancellationToken cancellationToken)
    {
        try
        {
            var result = await _resolutionService.ResolveAsync(
                request.ProductUrl,
                cancellationToken);

            return Ok(result);
        }
        catch (ArgumentException exception)
        {
            return BadRequest(new { message = exception.Message });
        }
        catch (HttpRequestException exception)
        {
            _logger.LogError(exception, "Unable to retrieve product information from the scraper service.");
            return StatusCode(
                StatusCodes.Status502BadGateway,
                new { message = "Unable to retrieve product information from the scraper service." });
        }
        catch (InvalidOperationException exception)
        {
            _logger.LogError(
                exception,
                "Product resolution failed.");

            return StatusCode(
                StatusCodes.Status502BadGateway,
                new
                {
                    message = "Unable to resolve product information."
                });
        }
    }

    [HttpPost]
    [ProducesResponseType(typeof(ProductResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<ActionResult<ProductResponse>> Create(
        [FromBody] CreateProductRequest request,
        CancellationToken cancellationToken)
    {
        try
        {
            var product = await _productService.CreateAsync(
                request.ProductUrl,
                request.Platform,
                request.Title,
                request.ExternalProductId,
                cancellationToken);

            var response = new ProductResponse
            {
                Id = product.Id,
                ProductUrl = product.ProductUrl,
                Platform = product.Platform,
                ExternalProductId = product.ExternalProductId,
                Title = product.Title,
                CreatedAtUtc = product.CreatedAtUtc
            };

            return CreatedAtAction(
                nameof(GetById),
                new { id = product.Id },
                response);
        }
        catch (InvalidOperationException ex)
        {
            return Conflict(new { message = ex.Message });
        }
    }

    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(ProductResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ProductResponse>> GetById(
        Guid id,
        CancellationToken cancellationToken)
    {
        var product = await _productService.GetByIdAsync(
            id,
            cancellationToken);

        if (product is null)
        {
            return NotFound();
        }

        var response = new ProductResponse
        {
            Id = product.Id,
            ProductUrl = product.ProductUrl,
            Platform = product.Platform,
            ExternalProductId = product.ExternalProductId,
            Title = product.Title,
            CreatedAtUtc = product.CreatedAtUtc
        };

        return Ok(response);
    }

    [HttpPost("{productId:guid}/refresh")]
    public async Task<IActionResult> RefreshProduct(
        Guid productId,
        CancellationToken cancellationToken)
    {
        var processedVariants = await _monitoringService.RefreshProductAsync(
            productId,
            cancellationToken
        );

        return Ok(new
        {
            message = "Product refreshed successfully.",
            productId,
            processedVariants
        });
    }
}
