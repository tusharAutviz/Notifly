"""
Patch for passlib to work with newer versions of bcrypt.
Import this module before using passlib to apply the patch.
"""
import logging
import sys

logger = logging.getLogger(__name__)

def patch_passlib_bcrypt():
    """
    Patch passlib.handlers.bcrypt to work with newer versions of bcrypt.
    This is needed because passlib expects bcrypt to have an __about__ attribute,
    but newer versions of bcrypt have changed their structure.
    """
    try:
        import bcrypt
        import passlib.handlers.bcrypt

        # Check if bcrypt has the __about__ attribute
        if not hasattr(bcrypt, '__about__'):
            # Create a fake __about__ module with a __version__ attribute
            class FakeAbout:
                __version__ = bcrypt.__version__

            # Attach it to bcrypt
            bcrypt.__about__ = FakeAbout()
            
            logger.info(f"Patched passlib to work with bcrypt {bcrypt.__version__}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to patch passlib: {str(e)}")
        return False

# Apply the patch when this module is imported
patch_result = patch_passlib_bcrypt()
