
using ProductIntelligence.Core.Products.DTOs;

namespace ProductIntelligence.Core.Tests;

public static class FakeScrapedProductData
{
    public static ScrapedProductDto GetProduct()
    {
        return new ScrapedProductDto
        {
            Title = "ASICS GEL-PULSE 16 Running Shoes For Men",
            Brand = "ASICS",

            Colors =
            [
                new ColorVariantDto
                {
                    Color = "Black",
                    Pid = "00C0030B-14FD-4E00-B44D-47B732484B98",

                    Sizes =
                    [
                        new SizeVariantDto
                        {
                            Size = "UK 7",
                            Pid = "BLACK_SIZE_7",
                            Available = true,
                            Price = 4999
                        },
                        new SizeVariantDto
                        {
                            Size = "UK 8",
                            Pid = "BLACK_SIZE_8",
                            Available = true,
                            Price = 4999
                        },
                        new SizeVariantDto
                        {
                            Size = "UK 9",
                            Pid = "BLACK_SIZE_9",
                            Available = false,
                            Price = 4999
                        },
                        new SizeVariantDto
                        {
                            Size = "UK 10",
                            Pid = "BLACK_SIZE_10",
                            Available = true,
                            Price = 4799
                        }
                    ]
                }
            ]
        };
    }
}
