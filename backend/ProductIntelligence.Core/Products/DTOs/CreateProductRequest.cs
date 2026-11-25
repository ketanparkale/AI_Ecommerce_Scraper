
using System.ComponentModel.DataAnnotations;

namespace ProductIntelligence.Core.Products.DTOs;

public class CreateProductRequest
{
    [Required]
    [Url]
    [StringLength(2048)]
    public string ProductUrl { get; set; } = string.Empty;

    [Required]
    [StringLength(50)]
    public string Platform { get; set; } = string.Empty;

    [Required]
    [StringLength(500)]
    public string Title { get; set; } = string.Empty;

    [StringLength(100)]
    public string? ExternalProductId { get; set; }
}
