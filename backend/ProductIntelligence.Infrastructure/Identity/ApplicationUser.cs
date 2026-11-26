
using Microsoft.AspNetCore.Identity;

namespace ProductIntelligence.Infrastructure.Identity;

public class ApplicationUser : IdentityUser<Guid>
{
    public string? FullName { get; set; }
}
