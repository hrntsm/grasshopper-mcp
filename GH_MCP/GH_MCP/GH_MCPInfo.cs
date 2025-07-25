using System;
using System.Drawing;
using Grasshopper.Kernel;

namespace GrasshopperMCP
{
    public class GH_MCPInfo : GH_AssemblyInfo
    {
        public override string Name => "GH_MCP";
        public override Bitmap Icon => null;
        public override string Description => "";
        public override Guid Id => new Guid("1b472cf6-015c-496a-a0a1-7ced4df994a3");
        public override string AuthorName => "";
        public override string AuthorContact => "";
        public override string AssemblyVersion => GetType().Assembly.GetName().Version.ToString();
    }
}
