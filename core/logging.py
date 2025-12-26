import logging

class LogHandler:
    """
    Configures and manages project loggers.
    
    Attributes:
        name (str): The name of the logger. If not specified, the module name (__name__) is used.
    """
    def __init__(self, name: str = None):
        """
        Initializes the LogHandler with a logger name (if provided).
        
        Args:
            name (str): The name to assign to the logger.
        """
        self.name = name

    def logger(self):
        """
        Creates and configures a logger with proper level and formats.
        
        Returns:
            logging.Logger: A configured logger instance ready for use.
        """
        # Get or create a logger
        name = self.name or __name__
        logger = logging.getLogger(name)
        
        # Set the logger to DEBUG level to capture all messages
        logger.setLevel(logging.DEBUG)
        
        # Create a console stream handler to output to stderr
        handler = logging.StreamHandler()
        
        # Define the log format
        formatter = logging.Formatter('%(asctime)s - %(levelname)s:     %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        # Apply the formatter to the handler
        handler.setFormatter(formatter)
        
        # Attach the handler to the logger
        logger.addHandler(handler)

        return logger