namespace GH_MCP.Models
{
    /// <summary>
    /// Represents a component connection endpoint
    /// </summary>
    public class Connection
    {
        /// <summary>
        /// Component GUID
        /// </summary>
        public string ComponentId { get; set; }

        /// <summary>
        /// Parameter name (input or output parameter)
        /// </summary>
        public string ParameterName { get; set; }

        /// <summary>
        /// Parameter index (use index if name is not specified)
        /// </summary>
        public int? ParameterIndex { get; set; }

        /// <summary>
        /// Check if connection is valid
        /// </summary>
        public bool IsValid()
        {
            return !string.IsNullOrEmpty(ComponentId) &&
                   (!string.IsNullOrEmpty(ParameterName) || ParameterIndex.HasValue);
        }
    }

    /// <summary>
    /// Represents a connection between two components
    /// </summary>
    public class ConnectionPairing
    {
        /// <summary>
        /// Source component connection (output endpoint)
        /// </summary>
        public Connection Source { get; set; }

        /// <summary>
        /// Target component connection (input endpoint)
        /// </summary>
        public Connection Target { get; set; }

        /// <summary>
        /// Check if connection pairing is valid
        /// </summary>
        public bool IsValid()
        {
            return Source != null && Target != null && Source.IsValid() && Target.IsValid();
        }
    }
}
