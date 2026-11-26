using System.ComponentModel.DataAnnotations;

namespace ProductIntelligence.Core.Products.DTOs;

public class ResolveProductRequest
{
    [Required]
    [Url]
    [StringLength(2048)]
    public string ProductUrl { get; set; } = string.Empty;
}
