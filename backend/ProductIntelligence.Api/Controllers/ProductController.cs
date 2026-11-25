
using Microsoft.AspNetCore.Mvc;
using ProductIntelligence.Core.Products.DTOs;
using ProductIntelligence.Core.Products.Services;

namespace ProductIntelligence.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ProductsController : ControllerBase
{
    private readonly ProductService _productService;
    private readonly ProductMonitoringService _monitoringService;

    public ProductsController(
        ProductService productService,
        ProductMonitoringService monitoringService)
    {
        _productService = productService;
        _monitoringService = monitoringService;
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
