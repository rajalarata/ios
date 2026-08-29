import OSLog

protocol AppLogging: Sendable {
    func debug(_ message: String)
    func info(_ message: String)
    func error(_ message: String)
}

struct AppLogger: AppLogging {
    private let logger: Logger

    init(category: String) {
        logger = Logger(subsystem: "com.rajalarata.ios", category: category)
    }

    func debug(_ message: String) {
        logger.debug("\(message, privacy: .public)")
    }

    func info(_ message: String) {
        logger.info("\(message, privacy: .public)")
    }

    func error(_ message: String) {
        logger.error("\(message, privacy: .public)")
    }
}
