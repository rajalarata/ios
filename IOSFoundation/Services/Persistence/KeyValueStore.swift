import Foundation

protocol KeyValueStore: Sendable {
    func data(forKey key: String) async -> Data?
    func set(_ data: Data?, forKey key: String) async
}

actor UserDefaultsStore: KeyValueStore {
    private let defaults: UserDefaults

    init(suiteName: String? = nil) {
        if let suiteName, let defaults = UserDefaults(suiteName: suiteName) {
            self.defaults = defaults
        } else {
            defaults = .standard
        }
    }

    func data(forKey key: String) -> Data? {
        defaults.data(forKey: key)
    }

    func set(_ data: Data?, forKey key: String) {
        defaults.set(data, forKey: key)
    }
}
