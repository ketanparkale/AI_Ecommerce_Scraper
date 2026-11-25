namespace ProductIntelligence.Core.Products.DTOs;

public class ColorVariantDto
{
    public string Color { get; set; } = string.Empty;
    public string Pid { get; set; } = string.Empty;
    public List<SizeVariantDto> Sizes { get; set; } = [];
}