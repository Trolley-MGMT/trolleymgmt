let p = new Promise((resolve, reject) => {
    let a = 1 + 2
    if (a == 2) {
        resolve('Success')
    } else {
        resolve('Failure')}
})

p.then((message) => {
    console.log('This is a then message: ' + message)
}).catch((message) => {
    console.log('This is a catch message: ' + message)
})