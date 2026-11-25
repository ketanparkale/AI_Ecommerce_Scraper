namespace ProductIntelligence.Core.Products.DTOs;

public class SizeVariantDto
{
    public string Size { get; set; } = string.Empty;
    public string Pid { get; set; } = string.Empty;
    public bool Available { get; set; }
    public decimal? Price { get; set; }
}