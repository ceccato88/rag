"""Multi-agent research system."""

__version__ = "0.1.0"

# Enhanced system components (optional import)
try:
    from .enhanced import (
        EnhancedRAGSystem,
        EnhancedLeadResearcher,
        create_enhanced_lead_researcher,
        integrate_enhanced_system
    )
    __all__ = [
        'EnhancedRAGSystem',
        'EnhancedLeadResearcher', 
        'create_enhanced_lead_researcher',
        'integrate_enhanced_system'
    ]
except ImportError:
    # Enhanced system not available
    __all__ = []